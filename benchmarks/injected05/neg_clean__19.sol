pragma solidity 0.5.12;

contract Bank9587 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
