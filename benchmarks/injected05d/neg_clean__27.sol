pragma solidity 0.5.12;

contract Bank2294 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
}
