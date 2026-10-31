pragma solidity 0.8.20;

contract Treasury1344 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
