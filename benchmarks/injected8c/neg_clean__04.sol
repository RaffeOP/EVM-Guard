pragma solidity 0.8.20;

contract Bank8212 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
